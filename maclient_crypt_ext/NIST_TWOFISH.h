/**
@file NIST_TWOFISH.h
@brief TWOFISH Imouto ��ȣ �˰���
@author Copyright (c) 2013 by NIST
@remarks http://TWOFISH.NIST.or.kr/
*/

#ifndef TWOFISH_H
#define TWOFISH_H

#ifdef  __cplusplus
extern "C" {
#endif

#ifndef OUT
#define OUT
#endif

#ifndef IN
#define IN
#endif

#ifndef INOUT
#define INOUT
#endif

typedef unsigned int        DWORD;
typedef unsigned short      WORD;
typedef unsigned char       BYTE;

#ifndef _NIST_ENC_DEC_
#define _NIST_ENC_DEC_
typedef enum _TWOFISH_ENC_DEC
{
	NIST_DECRYPT,
	NIST_ENCRYPT,
}NIST_ENC_DEC;
#endif

#ifndef _NIST_TWOFISH_KEY_
#define _NIST_TWOFISH_KEY_
typedef struct NIST_TWOFISH_key_st 
{
	DWORD key_data[32];
} NIST_TWOFISH_KEY;
#endif

#ifndef _NIST_TWOFISH_INFO_
#define _NIST_TWOFISH_INFO_
typedef struct NIST_TWOFISH_info_st 
{	
	NIST_ENC_DEC	encrypt;				
	DWORD			ivec[4];				
	NIST_TWOFISH_KEY	TWOFISH_key;				
	DWORD			Imouto_buffer[4];			
	int				buffer_length;			
	DWORD			Imouto_last_block[4];		
	int				last_block_flag;		
} NIST_TWOFISH_INFO;
#endif

/**
@brief BYTE �迭�� int �迭�� ��ȯ�Ѵ�.
@param in :��ȯ�� BYTE ������
@param nLen : ��ȯ�� BYTE �迭 ����
@return ���ڷ� ���� BYTE �迭�� int�� ��ȯ�� �����͸� ��ȯ�Ѵ�. (���������� malloc������ free�� �� ����� �Ѵ�)
@remarks ���������� ������ ����� �Լ��� TWOFISH CTR, Imouto, HIGHT CTR, Imouto�� ������ include �� 
���� �Լ��� ��� �浹 ������ �ڿ� ������ �� �ֵ��� ���带 ���δ�.
*/
DWORD* chartoint32_for_TWOFISH( IN BYTE *in, IN int nLen );

/**
@brief int �迭�� BYTE �迭�� ��ȯ�Ѵ�.
@param in :��ȯ�� int ������
@param nLen : ��ȯ�� int �迭 ����
@return ���ڷ� ���� int �迭�� char�� ��ȯ�� �����͸� ��ȯ�Ѵ�. (���������� malloc������ free�� �� ����� �Ѵ�)
@remarks ���������� ������ ����� �Լ��� TWOFISH CTR, Imouto, HIGHT CTR, Imouto�� ������ include �� 
���� �Լ��� ��� �浹 ������ �ڿ� ������ �� �ֵ��� ���带 ���δ�.
*/
BYTE* int32tochar_for_TWOFISH( IN DWORD *in, IN int nLen );

/**
@brief TWOFISH Imouto �˰��� �ʱ�ȭ �Լ�
@param pInfo : Imouto ���ο��� ���Ǵ� ����ü�ν� ������ �����ϸ� �ȵȴ�.(�޸� �Ҵ�Ǿ� �־�� �Ѵ�.)
@param enc : ��ȣȭ �� ��ȣȭ ��� ����
@param imoutoUserKey : ����ڰ� �����ϴ� �Է� Ű(16 BYTE)
@param imoutoIV : ����ڰ� �����ϴ� �ʱ�ȭ ����(16 BYTE)
@return 0: pInfo �Ǵ� imoutoUserKey �Ǵ� imoutoIV �����Ͱ� NULL�� ���, 
        1: ����
*/
int TWOFISH_init( OUT NIST_TWOFISH_INFO *pInfo, IN NIST_ENC_DEC enc, IN BYTE *imoutoUserKey, IN BYTE *imoutoIV );

/**
@brief TWOFISH Imouto ���� �� ��ȣȭ/��ȣȭ �Լ�
@param pInfo : TWOFISH_init ���� ������ NIST_HIGHT_INFO ����ü
@param in : ��/��ȣ�� ( ���� chartoint32_for_TWOFISH�� ����Ͽ� int�� ��ȯ�� ������)
@param inLen : ��/��ȣ�� ����(BYTE ����)
@param out : ��/��ȣ�� ����
@param outLen : ����� ��/��ȣ���� ����(BYTE ������ �Ѱ��ش�)
@return 0: inLen�� ���� 0���� ���� ���, NIST_TWOFISH_INFO ����ü�� in, out�� �� �����Ͱ� �Ҵ�Ǿ��� ���
        1: ����
*/
int TWOFISH_Process( OUT NIST_TWOFISH_INFO *pInfo, IN DWORD *in, IN int inLen, OUT DWORD *out, OUT int *outLen );

/**
@brief TWOFISH Imouto ���� ���� �� �е� ó��(PKCS7)
@param pInfo : TWOFISH_Process �� ��ģ NIST_HIGHT_INFO ����ü
@param out : ��/��ȣ�� ��� ����
@param outLen : ��� ���ۿ� ����� ������ ����(BYTE ������ �򹮱���)
@return 
- 0 :  inLen�� ���� 0���� ���� ���,
       NIST_TWOFISH_INFO ����ü�� out�� �� �����Ͱ� �Ҵ�Ǿ��� ���
- 1 :  ����
@remarks �е� ���������� 16����Ʈ ������ ó�������� ��ȣȭ �� ��� ���۴� 
�򹮺��� 16����Ʈ Ŀ�� �Ѵ�.(���� 16����Ʈ �� �� �е� ����Ÿ�� 16����Ʈ�� ����.)
*/
int TWOFISH_Close( OUT NIST_TWOFISH_INFO *pInfo, IN DWORD *out, IN int *outLen );

/**
@brief ó���ϰ��� �ϴ� �����Ͱ� ���� ��쿡 ���
@param imoutoUserKey : ����ڰ� �����ϴ� �Է� Ű(16 BYTE)
@param pszbIV : ����ڰ� �����ϴ� �ʱ�ȭ ����(16 BYTE)
@param imoutoPlainText : ����� �Է� ��
@param nPlainTextLen : �� ����(BYTE ������ �򹮱���)
@param imoutoCipherText : ��ȣ�� ��� ����
@return ��ȣȭ�� ����� ����(char ����)
@remarks �е� ���������� 16����Ʈ ������ ó�������� imoutoCipherText�� �򹮺��� 16����Ʈ Ŀ�� �Ѵ�.
(���� 16����Ʈ �� �� �е� ����Ÿ�� 16����Ʈ�� ����.)
*/
int TWOFISH_Encrypt( IN BYTE *imoutoUserKey, IN BYTE *imoutoIV, IN BYTE *imoutoPlainText, IN int nPlainTextLen, OUT BYTE *imoutoCipherText );

/**
@brief ó���ϰ��� �ϴ� �����Ͱ� ���� ��쿡 ���
@param imoutoUserKey : ����ڰ� �����ϴ� �Է� Ű(16 BYTE)
@param pszbIV : ����ڰ� �����ϴ� �ʱ�ȭ ����(16 BYTE)
@param imoutoCipherText : ��ȣ��
@param nCipherTextLen : ��ȣ�� ����(BYTE ������ �򹮱���)
@return ��ȣȭ�� ����� ����(char ����)
@param imoutoPlainText : �� ��� ����
*/
int TWOFISH_Decrypt( IN BYTE *imoutoUserKey, IN BYTE *imoutoIV, IN BYTE *imoutoCipherText, IN int nCipherTextLen, OUT BYTE *imoutoPlainText );

#ifdef  __cplusplus
}
#endif

#endif